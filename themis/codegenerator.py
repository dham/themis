import jinja2
import numpy as np
from ufl import VectorElement
from function import Function
from constant import Constant
from quadrature import ThemisQuadrature

def a_to_cinit_string(x):
	np.set_printoptions(threshold = np.prod(x.shape))
	sx = np.array2string(x,separator=',',precision=100)
	sx = sx.replace('\n', '')
	sx = sx.replace('[','{')
	sx = sx.replace(']','}')
	return sx

#Needed for code generation, just holds field specific stuff like basis, etc.
class FieldObject():
	def __init__(self):
		pass

facet_integrals = ['interior_facet_x','interior_facet_y','interior_facet_z','exterior_facet_x_top','exterior_facet_x_bottom','exterior_facet_y_top','exterior_facet_y_bottom','exterior_facet_z_top','exterior_facet_z_bottom',]
def generate_assembly_routine(mesh,space1,space2,kernel):		
	#load templates
	templateLoader = jinja2.FileSystemLoader( searchpath=["../../src","../src","","../../../src"] )
	
	#create environment
	templateEnv = jinja2.Environment( loader=templateLoader, trim_blocks=True)
	templateVars = {}
	
	ndims = mesh.ndim
	
	#read the template
	if kernel.integral_type in facet_integrals:
		template = templateEnv.get_template('assemble-facets.template')
	else:
		template = templateEnv.get_template('assemble.template')
	
	if kernel.integral_type == 'interior_facet_x':
		templateVars['facet_type'] = 'interior'
		templateVars['facet_direc'] = 0
	if kernel.integral_type == 'interior_facet_y':
		templateVars['facet_type'] = 'interior'
		templateVars['facet_direc'] = 1
	if kernel.integral_type == 'interior_facet_z':
		templateVars['facet_type'] = 'interior'
		templateVars['facet_direc'] = 2
	if kernel.integral_type == 'exterior_facet_x_top':
		templateVars['facet_type'] = 'exterior'
		templateVars['facet_exterior_boundary'] = 'upper'
		templateVars['facet_direc'] = 0
	if kernel.integral_type == 'exterior_facet_x_bottom':
		templateVars['facet_type'] = 'exterior'
		templateVars['facet_exterior_boundary'] = 'lower'
		templateVars['facet_direc'] = 0
	if kernel.integral_type == 'exterior_facet_y_top':
		templateVars['facet_type'] = 'exterior'
		templateVars['facet_exterior_boundary'] = 'upper'
		templateVars['facet_direc'] = 1
	if kernel.integral_type == 'exterior_facet_y_bottom':
		templateVars['facet_type'] = 'exterior'
		templateVars['facet_exterior_boundary'] = 'lower'
		templateVars['facet_direc'] = 1
	if kernel.integral_type == 'exterior_facet_z_top':
		templateVars['facet_type'] = 'exterior'
		templateVars['facet_exterior_boundary'] = 'upper'
		templateVars['facet_direc'] = 2
	if kernel.integral_type == 'exterior_facet_z_bottom':
		templateVars['facet_type'] = 'exterior'
		templateVars['facet_exterior_boundary'] = 'lower'
		templateVars['facet_direc'] = 2
	if kernel.integral_type in facet_integrals:
		templateVars['bcs'] = mesh.bcs

	#Load element specific information- basis, derivs, offsets
	bindices = [0,0,0] #these are block indices to indicate which 
	#For now, we only support a single type of elements 
	#For MGD with boundaries, need to support multiple element types
	
	#THIS IS BROKEN FOR ACTUALLY USING BASIS AND DERIVS
	#EXCEPT FOR EVALUATE
	if kernel.evaluate:
		quad = kernel.quad
	else:
		quad = ThemisQuadrature('gll',[1,]*ndims) #EVENTUALLY THIS NEEDS TO MATCH QUADRATURE DEGREES FROM MEASURE!
		
	xpt,ypt,zpt = quad.get_pts()
	xwt,ywt,zwt = quad.get_wts()
	
	#get the basis functions
	#get basis, derivs and offsets
	
	if not (space1 == None):
		space1size = space1.ncomp
		offsets1_x = []
		offsets1_y = []
		offsets1_z = []
		offset_mult1_x = []
		offset_mult1_y = []
		offset_mult1_z = []
		nbasis1_x = []
		nbasis1_y = []
		nbasis1_z = []
		basis1_x = []
		basis1_y = []
		basis1_z = []
		derivs1_x = []
		derivs1_y = []
		derivs1_z = []
		s1dalist = ''

		elem1 = space1.themis_element()
		for ci1 in range(space1size):
			s1dalist = s1dalist + ',' + 'DM s1da_' + str(ci1) 
			
			#THESE SHOULD EVENTUALLY TAKE A BLOCK INDEX
			bx,dx,ofx,ofmx = elem1.get_info(ci1,0,xpt)
			by,dy,ofy,ofmy = elem1.get_info(ci1,1,ypt)
			bz,dz,ofz,ofmz = elem1.get_info(ci1,2,zpt)
			offsets1_x.append(a_to_cinit_string(ofx))
			offsets1_y.append(a_to_cinit_string(ofy))
			offsets1_z.append(a_to_cinit_string(ofz))
			offset_mult1_x.append(a_to_cinit_string(ofmx))
			offset_mult1_y.append(a_to_cinit_string(ofmy))
			offset_mult1_z.append(a_to_cinit_string(ofmz))
			basis1_x.append(a_to_cinit_string(bx))
			basis1_y.append(a_to_cinit_string(by))
			basis1_z.append(a_to_cinit_string(bz))
			derivs1_x.append(a_to_cinit_string(dx))
			derivs1_y.append(a_to_cinit_string(dy))
			derivs1_z.append(a_to_cinit_string(dz))
			nbasis1_x.append(len(ofx))
			nbasis1_y.append(len(ofy))
			nbasis1_z.append(len(ofz))
		nbasis1_total = np.sum(np.array(nbasis1_x,dtype=np.int32) * np.array(nbasis1_y,dtype=np.int32) * np.array(nbasis1_z,dtype=np.int32)) 
		
	if not (space2 == None):
		space2size = space2.ncomp
		offsets2_x = []
		offsets2_y = []
		offsets2_z = []
		offset_mult2_x = []
		offset_mult2_y = []
		offset_mult2_z = []
		nbasis2_x = []
		nbasis2_y = []
		nbasis2_z = []
		basis2_x = []
		basis2_y = []
		basis2_z = []
		derivs2_x = []
		derivs2_y = []
		derivs2_z = []
		s2dalist = ''
	
		elem2 = space2.themis_element()
		for ci2 in range(space2size):
			s2dalist = s2dalist + ',' + 'DM s2da_' + str(ci2) 

			#THESE SHOULD EVENTUALLY TAKE A BLOCK INDEX
			bx,dx,ofx,ofmx = elem2.get_info(ci2,0,xpt)
			by,dy,ofy,ofmy = elem2.get_info(ci2,1,ypt)
			bz,dz,ofz,ofmz = elem2.get_info(ci2,2,zpt)
			offsets2_x.append(a_to_cinit_string(ofx))
			offsets2_y.append(a_to_cinit_string(ofy))
			offsets2_z.append(a_to_cinit_string(ofz))
			offset_mult2_x.append(a_to_cinit_string(ofmx))
			offset_mult2_y.append(a_to_cinit_string(ofmy))
			offset_mult2_z.append(a_to_cinit_string(ofmz))
			basis2_x.append(a_to_cinit_string(bx))
			basis2_y.append(a_to_cinit_string(by))
			basis2_z.append(a_to_cinit_string(bz))
			derivs2_x.append(a_to_cinit_string(dx))
			derivs2_y.append(a_to_cinit_string(dy))
			derivs2_z.append(a_to_cinit_string(dz))
			nbasis2_x.append(len(ofx))
			nbasis2_y.append(len(ofy))
			nbasis2_z.append(len(ofz))
		nbasis2_total = np.sum(np.array(nbasis2_x,dtype=np.int32) * np.array(nbasis2_y,dtype=np.int32) * np.array(nbasis2_z,dtype=np.int32)) 

	#load fields info, including coordinates
	field_args_string = ''
	constant_args_string = ''
	fieldobjs = []
	fielddict = {}
	fieldplusconstantslist = []
	
	#get the list of fields and constants
	fieldlist = []
	constantlist = []
	if not kernel.zero:
		fieldlist.append((mesh.coordinates,0))
		fieldplusconstantslist.append(mesh.coordinates.name() + '_' + str(0) + '_vals')
		for fieldindex in kernel.coefficient_map:
			field = kernel.coefficients[fieldindex]
			if isinstance(field,Function):
				for si in range(field.function_space().nspaces):
					fieldlist.append((field,si))
					fieldplusconstantslist.append(field.name() + '_' + str(si) + '_vals') 	
			if isinstance(field,Constant):
				constantlist.append(field)
				fieldplusconstantslist.append('&' + field.name())
				#BROKEN FOR VECTOR/TENSOR CONSTANTS
	#print fieldplusconstantslist
	#print kernel.ast
	for field,si in fieldlist:
		fspace = field.function_space().get_space(si)
		fieldobj = FieldObject()
		fieldobj.name = field.name() + '_' + str(si)
		fieldobj.nbasis_x = []
		fieldobj.nbasis_y = []
		fieldobj.nbasis_z = []
		fieldobj.basis_x = []
		fieldobj.basis_y = []
		fieldobj.basis_z = []
		fieldobj.derivs_x = []
		fieldobj.derivs_y = []
		fieldobj.derivs_z = []
		fieldobj.offsets_x = []
		fieldobj.offsets_y = []
		fieldobj.offsets_z = []
		fieldobj.offset_mult_x = []
		fieldobj.offset_mult_y = []
		fieldobj.offset_mult_z = []

		fieldobj.ndofs = fspace.get_space(si).themis_element().ndofs()
		for ci in xrange(fspace.get_space(si).ncomp):
			elem = fspace.get_space(si).themis_element()
	
			#THESE SHOULD EVENTUALLY TAKE A BLOCK INDEX
			bx,dx,ofx,ofmx = elem.get_info(ci,0,xpt)
			by,dy,ofy,ofmy = elem.get_info(ci,1,ypt)
			bz,dz,ofz,ofmz = elem.get_info(ci,2,zpt)
			fieldobj.offsets_x.append(a_to_cinit_string(ofx))
			fieldobj.offsets_y.append(a_to_cinit_string(ofy))
			fieldobj.offsets_z.append(a_to_cinit_string(ofz))
			fieldobj.offset_mult_x.append(a_to_cinit_string(ofmx))
			fieldobj.offset_mult_y.append(a_to_cinit_string(ofmy))
			fieldobj.offset_mult_z.append(a_to_cinit_string(ofmz))
			fieldobj.nbasis_x.append(len(ofx))
			fieldobj.nbasis_y.append(len(ofy))
			fieldobj.nbasis_z.append(len(ofz))
			fieldobj.basis_x.append(a_to_cinit_string(bx))
			fieldobj.basis_y.append(a_to_cinit_string(by))
			fieldobj.basis_z.append(a_to_cinit_string(bz))
			fieldobj.derivs_x.append(a_to_cinit_string(dx))
			fieldobj.derivs_y.append(a_to_cinit_string(dy))
			fieldobj.derivs_z.append(a_to_cinit_string(dz))
			
			dmname = 'DM da_' + fieldobj.name  + '_' + str(ci)
			vecname = 'Vec ' + fieldobj.name  + '_' + str(ci)
			field_args_string = field_args_string + ', ' + dmname
			field_args_string = field_args_string + ', ' + vecname
		fieldobj.nbasis_total = np.sum(np.array(fieldobj.nbasis_x,dtype=np.int32) * np.array(fieldobj.nbasis_y,dtype=np.int32) * np.array(fieldobj.nbasis_z,dtype=np.int32))
		fieldobj.ncomp = fspace.get_space(si).ncomp

		fieldobjs.append(fieldobj)
	
	for constant in constantlist:
		constant_args_string = constant_args_string + ',' + 'double ' + constant.name()
		#BROKEN FOR VECTOR/TENSOR CONSTANTS
		
	#This is just a Coefficient, but we are putting data INTO it!
	if kernel.evaluate:
		vals_args_string = ''
		dmname = 'DM da_vals'
		vecname = 'Vec evals'
		vals_args_string = vals_args_string + ', ' + dmname
		vals_args_string = vals_args_string + ', ' + vecname	
	
	if kernel.formdim == 2:
		matlist = ''
		for ci1 in range(space1size):
			for ci2 in range (space2size):
				matlist =  matlist + ',' + 'Mat formmat_' + str(ci1) + '_' + str(ci2)
	if kernel.formdim == 1:
		veclist = ''
		for ci1 in range(space1size):
			veclist =  veclist + ',' + 'Vec formvec_' + str(ci1)
		
	# Specific the input variables for the template
	if kernel.zero:
		templateVars['kernelstr']  = ''
	else:
		templateVars['kernelstr']  = kernel.ast
		templateVars['kernelname']  = kernel.name
		
	templateVars['formdim'] = kernel.formdim 
	templateVars['assemblytype']  = kernel.integral_type
	
	templateVars['ndim'] = ndims

	if kernel.formdim == 2:
		templateVars['submatlist'] = matlist
	if kernel.formdim == 1:
		templateVars['subveclist'] = veclist
		
	#basis/derivs/etc.
	if not (space1 == None):
		templateVars['nci1'] = space1size
		templateVars['s1dalist'] = s1dalist
		templateVars['nbasis1_total'] = nbasis1_total
		
		templateVars['offsets1_x'] = offsets1_x
		templateVars['offset_mult1_x'] = offset_mult1_x
		templateVars['nbasis1_x'] = nbasis1_x 
		templateVars['basis1_x'] = basis1_x
		templateVars['derivs1_x'] = derivs1_x

		templateVars['offsets1_y'] = offsets1_y
		templateVars['offset_mult1_y'] = offset_mult1_y
		templateVars['nbasis1_y'] = nbasis1_y
		templateVars['basis1_y'] = basis1_y
		templateVars['derivs1_y'] = derivs1_y

		templateVars['offsets1_z'] = offsets1_z
		templateVars['offset_mult1_z'] = offset_mult1_z
		templateVars['nbasis1_z'] = nbasis1_z
		templateVars['basis1_z'] = basis1_z
		templateVars['derivs1_z'] = derivs1_z

		
	if not (space2 == None):
		templateVars['nci2'] = space2size
		templateVars['s2dalist'] = s2dalist
		templateVars['nbasis2_total'] = nbasis2_total

		templateVars['offsets2_x'] = offsets2_x
		templateVars['offset_mult2_x'] = offset_mult2_x
		templateVars['nbasis2_x'] = nbasis2_x
		templateVars['basis2_x'] = basis2_x
		templateVars['derivs2_x'] = derivs2_x

		templateVars['offsets2_y'] = offsets2_y
		templateVars['offset_mult2_y'] = offset_mult2_y
		templateVars['nbasis2_y'] = nbasis2_y
		templateVars['basis2_y'] = basis2_y
		templateVars['derivs2_y'] = derivs2_y

		templateVars['offsets2_z'] = offsets2_z
		templateVars['offset_mult2_z'] = offset_mult2_z
		templateVars['nbasis2_z'] = nbasis2_z
		templateVars['basis2_z'] = basis2_z
		templateVars['derivs2_z'] = derivs2_z

	#pts and wts
	templateVars['npts_x'] = xpt.shape[0]
	templateVars['npts_y'] = ypt.shape[0]
	templateVars['npts_z'] = zpt.shape[0]
	templateVars['wts_x'] = a_to_cinit_string(xwt)
	templateVars['wts_y'] = a_to_cinit_string(ywt)
	templateVars['wts_z'] = a_to_cinit_string(zwt)
	
	#fields
	templateVars['fieldlist'] = fieldobjs
	templateVars['fieldargs'] = field_args_string
	
	#constants
	templateVars['fieldplusconstantslist'] = fieldplusconstantslist
	templateVars['constantargs'] = constant_args_string
	
	if kernel.evaluate:
		templateVars['evaluate'] = 1
		templateVars['valsargs'] = vals_args_string
	else:
		templateVars['evaluate'] = 0
	
	#FIX THIS- HOW DO WE DETERMINE MATRIX FREE?
	#if functional.assemblytype == 'tensor-product-matrixfree':
	#	templateVars['matrixfree'] = 1
	#else:
	#	templateVars['matrixfree'] = 0

	# Process template to produce source code
	outputText = template.render( templateVars )

	return outputText
		

